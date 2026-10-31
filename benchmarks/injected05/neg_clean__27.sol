pragma solidity 0.5.12;

contract Fund7158 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }

    function totalDeposits() public view returns (uint256) { return supply; }

    function ownerOf_() public view returns (address) { return owner; }
}
