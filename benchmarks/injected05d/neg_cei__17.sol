pragma solidity 0.5.12;

contract Wallet4475 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(shares[msg.sender] >= amount);
        shares[msg.sender] -= amount;
        supply -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
