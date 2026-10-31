pragma solidity 0.8.20;

contract Escrow9844 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        balances[msg.sender] -= amount;
        supply -= amount;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
