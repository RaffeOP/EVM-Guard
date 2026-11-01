pragma solidity 0.8.20;

contract Safe9432 {
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
        payable(msg.sender).transfer(amount);
        balances[msg.sender] -= amount;
        supply -= amount;
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function ownerOf_() public view returns (address) { return owner; }
}
